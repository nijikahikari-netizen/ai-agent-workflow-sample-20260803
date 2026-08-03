# AI Agent Workflow Sample

폐기 가능한 P0 검증용 Spring Boot Sample Repository다. 실제 회사 정책이나 운영 데이터를 포함하지 않는다.

## Baseline 업무 정책

- `ACTIVE`: 신규 자산 대여 신청 허용
- `LEAVE`: Sample Repository의 기존 동작으로 신규 신청 허용
- `RESIGNED`: Baseline에서는 신규 신청이 허용되는 문제 상태
- 목표 변경: `RESIGNED`만 기존 `BusinessException` 계약으로 거부
- 변경 제외: DB Schema, 공개 HTTP API, `LEAVE` 정책, Workflow와 Dependency

## 로컬 검증

```powershell
.\gradlew.bat test --no-daemon
.\gradlew.bat spotlessCheck --no-daemon
python -m unittest discover scripts/tests -v
```

Java 21 Toolchain이 필요하다. Gradle은 Repository Wrapper를 사용한다.
