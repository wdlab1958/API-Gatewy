# API_Gateway 엔지니어링 감사 보고서

작성일: 2026-05-31
대상 경로: /home/ubuntu-02/ai_project/API_Gateway
수신: Brian

## 개요 (범위 + 한계)

- 본 감사는 단일 프로젝트 `API_Gateway`에 대한 읽기 전용 점검과 비파괴적 quick 검증(컴파일·import·lint·in-process 스모크 테스트)으로 한정한다.
- 스택(확인): Python FastAPI 기반 단일 게이트웨이. 의존성은 `fastapi`, `uvicorn`, `httpx`. 별도 패키징 파일 없음.
- 엔트리포인트(확인): `api_gateway_v2.py` (2,675행, `uvicorn.run(app, host="0.0.0.0", port=8080)`), 구버전 `api_gateway.py` (229행) 병존. 기동 스크립트는 `start_gateway.sh`가 `api_gateway_v2.py`를 실행한다.
- 한계: 백엔드 대상 서비스(포트 4001~ 등)는 기동하지 않았으므로 실제 프록시 왕복은 미검증이다. GPU/장기 서버 미사용 제약을 준수했다. `data/`, `.git/`는 건드리지 않았다. 실제 0.0.0.0 바인딩 외부 노출 기동은 수행하지 않았다(in-process TestClient만 사용).

## 실행·테스트 결과

- Python(확인): pyenv shim `python3` = 3.12.3, `/usr/bin/python3.12` = 3.12.3. 의존성 import 정상.
- 구문 컴파일(확인): `py_compile` — `api_gateway_v2.py`, `api_gateway.py` 모두 통과.
- 앱 로드(확인): `import api_gateway_v2` 성공, FastAPI 앱 라우트 14개.
- 스모크 테스트(확인, starlette TestClient): `/health` 200, `/` 200(대시보드 HTML 약 93KB), `/services` 200. `/api/services`는 404(해당 라우트 미존재 — 정상). `/health` 호출 시 게이트웨이가 백엔드로 실제 outbound httpx 요청을 발생시키는 것을 로그로 관찰.
- Lint(확인): `ruff --select F,E9` 결과 오류 9건 — 전부 F401(미사용 import). 전체 룰 기준 13건(F401 9 + E722 bare except 4). F821(미정의 이름)·E9(구문) 오류 없음.
- 단위 테스트(확인): 테스트 파일 없음(`*test*`, `conftest` 부재). CI 설정·Dockerfile·requirements.txt·pyproject.toml 모두 부재(확인).
- 종합 실행 판단: 의존성이 설치된 현재 환경에서 게이트웨이 자체는 기동 가능(runnable). 단, 대시보드의 "정상"은 백엔드 서비스들이 별도 기동되어 있어야 의미를 가진다.

## 발견된 문제점 (확인 vs 추정, 심각도)

1. (확인 / 중) CORS 설정 오류: `allow_origins=["*"]`와 `allow_credentials=True` 동시 사용(`api_gateway_v2.py` 약 1283~1287행). 브라우저 표준상 호환되지 않는 조합이며 보안 안티패턴이다.
2. (확인 / 중) 인증 부재 + 0.0.0.0 바인딩: 게이트웨이가 모든 인터페이스에 노출되며, 서비스 재기동(`/auto-recovery/...`)과 임의 백엔드 프록시(`/api/{service}/{path}`)에 인증·권한 검사가 없다. LAN 내 누구나 호출 가능.
3. (확인 / 중) 미사용 import 9건(F401). — 본 감사에서 조치 완료(아래 참조).
4. (확인 / 낮음) bare `except:` 4건(`api_gateway.py:72,79`, `api_gateway_v2.py:1328,2633`). 오류 은폐 가능. 동작에는 영향 없어 자동수정 미적용.
5. (확인 / 낮음) 잔존 브랜드 문자열: `10_start_all_services.sh`의 "A3Security" 2건. — 조치 완료.
6. (추정 / 중) 프록시의 비-JSON 응답 처리 손실: `proxy_request`가 content-type이 JSON이 아니면 응답을 `{"data": response.text, ...}`로 재포장한다(약 2630~2645행). 바이너리/HTML/스트리밍 응답은 원형 보존이 되지 않을 것으로 추정. 백엔드 미기동으로 실측 미검증.
7. (추정 / 낮음) 구버전 `api_gateway.py`와 신버전 `api_gateway_v2.py` 병존으로 인한 혼동·드리프트 위험. 어느 쪽이 정본인지 코드만으로는 단정 불가(스크립트는 v2 사용).
8. (추정 / 낮음) `subprocess.Popen(..., shell=True)`로 서비스 재기동(약 1161행). 명령은 내부 하드코딩 dict(`SERVICE_STARTUP_COMMANDS`)에서 오므로 외부 주입 경로는 확인되지 않음. 다만 shell=True 사용 자체는 권장되지 않음.

## 조치한 내용

- (확인) 브랜드 잔존 제거: `10_start_all_services.sh` 3행·56행 "A3Security" → "WDLAB@2023-2026"으로 수정. 재스캔 결과 `a3 security/a3sc/a3sec/aitf/에이쓰리` 잔존 NONE.
- (확인) 미사용 import 9건 자동 제거: `ruff --select F401 --fix` 적용(`api_gateway_v2.py`, `api_gateway.py`). 적용 후 `py_compile` 통과, `import` 성공(라우트 14개 유지), 스모크 `/health`·`/`·`/services` 모두 200으로 회귀 없음 확인.

참고: "a3de"/"A3-ADE"(A3-ADE Development Environment, 포트 4004/5004)는 코드 전반과 파일시스템 경로(`/home/ubuntu-02/ai_project/a3de/...`)에 의존하는 별개 제품 식별자이므로, 스크럽 대상 브랜드인지 불확실하고 경로 파손 위험이 있어 변경하지 않았다(미해결 항목 참조).

## 미해결·위험 항목 (권고만)

- CORS `allow_origins`를 명시적 허용 출처 목록으로 변경하거나 `allow_credentials=False`로 조정 권고. (위험: 동작 의존 클라이언트 영향 가능 → 미적용)
- 게이트웨이에 인증/접근제어 도입 또는 바인딩을 `127.0.0.1`로 제한 권고. 특히 서비스 재기동 엔드포인트. (운영 정책 결정 필요 → 미적용)
- "a3de"/"A3-ADE" 명칭이 스크럽 대상인지 Brian 확인 필요. 변경 시 코드 식별자·디렉터리 경로 동시 변경이 필요하여 위험. (확인 전 미적용)
- bare except 4건을 `except Exception`으로 좁히는 것 권고. (동작 영향 가능성 낮으나 검증 부담으로 미적용)
- 테스트·CI·의존성 명세(requirements.txt 등) 부재. 최소한 핵심 라우트 스모크 테스트와 의존성 고정 추가 권고.
- 프록시 비-JSON 응답 패스스루 정합성을 백엔드 기동 환경에서 실측 검증 권고.

## 종합 판단

게이트웨이 코드는 현재 환경에서 구문·로드·핵심 라우트 응답이 모두 정상으로, 자체 기동은 가능(확인)하다. 다만 단위 테스트·CI·패키징·Dockerfile이 전무하여 회귀 안전망이 없고, CORS 오설정과 무인증 0.0.0.0 노출이라는 운영 보안 약점이 확인된다. 본 감사에서는 검증 가능한 저위험 항목(브랜드 잔존 2건, 미사용 import 9건)만 수정 후 재검증을 완료했으며, 보안·구조 관련 변경은 동작 영향 우려로 권고에 그쳤다.

## 후속 조치 (2026-05-31)

Brian 승인 하에 보안 강화 후속 작업을 비파괴적으로 수행하고 실행 검증하였다(푸시·커밋·이력 변경 없음, `data/`·`.git/` 미접촉, `/usr/bin/python3.12` 사용).

- (확인 / 보안) CORS 오설정 시정: `allow_origins=["*"]`를 명시적 localhost 허용 목록(`http://localhost:8080`, `http://127.0.0.1:8080`, `http://localhost:3000`, `http://127.0.0.1:3000`)으로 교체하였다. 환경변수 `GATEWAY_CORS_ORIGINS`(쉼표 구분)로 재정의 가능하며, `allow_credentials=True`와의 비호환 와일드카드 조합을 제거하였다.
- (확인 / 보안) 인증 부재 시정: 환경변수 `GATEWAY_API_KEY` 기반 API-키 의존성(`require_api_key`, `X-API-Key` 헤더)을 도입하여 프록시 엔드포인트(`/api/{service}/{path}`)와 관리 엔드포인트(`POST /auto-recovery/reset/{service_key}`)에 적용하였다. 키 미설정 시 무인증으로 동작하여 하위 호환을 유지한다. 검증: 키 설정 시 헤더 없이 호출하면 두 엔드포인트 모두 401, 올바른 키 동반 시 인증 통과(백엔드 미기동으로 503, 401 아님)를 in-process TestClient로 확인하였다.
- (확인 / 보안) 바인딩 호스트 설정화: 하드코딩 `host="0.0.0.0"`를 환경변수 `GATEWAY_BIND_HOST`(기본값 `127.0.0.1`)로 변경하여 기본적으로 루프백에만 노출되도록 하였다. LAN 노출이 필요하면 `0.0.0.0`으로 재정의한다.
- (확인) bare `except:` 4건(`api_gateway.py` 2건, `api_gateway_v2.py` 2건)을 `except Exception:`으로 좁혔다. 재스캔 결과 bare except 잔존 NONE, `py_compile` 통과.
- (문서화 / 위험) `subprocess.Popen(..., shell=True)` 서비스 재기동(약 1159행)은 `cd`·`nohup`·백그라운드(`&`)·리다이렉션·명령 체이닝(`;`) 등 셸 기능에 의존하고, 명령 문자열은 내부 하드코딩 dict(`SERVICE_STARTUP_COMMANDS`)에서만 유래하여 외부 주입 경로가 없다. 인자 리스트 형태로의 단순·검증 가능한 변환이 불가하여(셸 의존), 회귀 위험을 고려해 변경하지 않고 문서화로 갈음한다.
- (확인 / MINOR) 의존성 명세 부재 해소: 실제 직접 import(`fastapi`, `uvicorn`, `httpx`)와 FastAPI 핵심 런타임 의존성(`pydantic`)을 기준으로 `requirements.txt`를 신설하였다(검증 환경 버전 기준 하한 핀).
- (확인 / MINOR) v1/v2 중복 정본 판정: `api_gateway_v2.py`가 정본이다(`start_gateway.sh`가 v2를 실행, 라우트 14개). `api_gateway.py`(v1)는 구버전으로 본 후속 작업에서는 bare except 시정만 적용하였다.

재검증 종합: 변경 후 `api_gateway_v2.py`·`api_gateway.py` 모두 `py_compile` 통과, `import api_gateway_v2` 성공(라우트 14개 유지), 스모크 `/health` 200 회귀 없음, API-키 401/통과 동작 확인 완료.
