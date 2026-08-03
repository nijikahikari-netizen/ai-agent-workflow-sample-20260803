# Repository 작업 규칙

## 범위

- 업무 변경은 승인된 `src/main/java/com/example/assetworkflow/asset/**`와 `src/test/java/com/example/assetworkflow/asset/**`에 한정한다.
- `.github/**`, `build.gradle`, `settings.gradle`, `gradle/**`, `src/main/resources/db/migration/**`는 별도 승인 없이 수정하지 않는다.
- DB Schema와 공개 HTTP API를 추가하지 않는다.
- `LEAVE`의 Baseline 허용 동작을 유지한다.

## 검증

- 관련 Test: `.\gradlew.bat test --tests '*AssetBorrowServiceTest' --no-daemon`
- 전체 Test: `.\gradlew.bat test --no-daemon`
- Format: `.\gradlew.bat spotlessCheck --no-daemon`
- Scope: `python scripts/scope_check.py --base <approved-base-sha> --policy .ai/scope-policy.json --output scope-result.json`

## 중지 조건

- 승인 경로 밖 수정이 필요하다.
- DB Schema·공개 API·Workflow·Dependency 변경이 필요하다.
- 기존 `BusinessException`·`ErrorCode` 계약을 유지할 수 없다.
- 요구가 `LEAVE` 정책을 새로 정의해야 한다.
