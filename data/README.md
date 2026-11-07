# 데이터 사전·계보

이 폴더의 CSV는 UTF-8 (BOM 없음), 첫 행 컬럼명, 한 기록 = 한 행을 원칙으로 한다. 데이터는 2026-11-07 대화에서 생성된 1차 엑셀의 내용을 바탕으로 **2018 향토지명집 pp.13–14 PDF 지면과 재대조하여 정정한 버전**이다. 원본 1911 필사본을 직접 판독한 학술 전사본은 아니다.

## 자료 목록

- `toponyms.csv`: 고정 ID 37행 = 4 옛 마을(`village`) + 21 골짜기(`valley`) + 8 들판(`field`) + 4 별도 기록(`unmatched_citation`). 출처 `SRC-001`.
- `control_points.csv`: 과거 조사에서 찾은 현대 위치 기준점 4행. 역사 유적/옛 동리의 좌표가 아님. 정확성은 **공식 위치자료 재검증 대기**.
- `sources.csv`: 출처·원본 확보 상태. `SRC-008`(1911 원본), `SRC-009`(지적원도)는 미확보.
- `claims.csv`: 주장별 증거상태·공간상태·다음 검증 작업.

## 지명 데이터 컬럼

| 필드 | 의미 |
|---|---|
| `toponym_id` | `GUL-001` 형식 영구 ID; 다른 지명에 재사용 금지 |
| `name` | 2018 자료집 표제어를 기준으로 정규화한 이름 |
| `feature_type` | village / valley / field / unmatched_citation |
| `hanja_2018` | 본문에서 직접 표기한 한자(없으면 빈 칸) |
| `quoted_1911_hanja` | **2018 편찬물이 인용한** 1911 한자 표기 |
| `quoted_1911_village` | **2018 편찬물이 인용한** 소속 동리 (복수 가능) |
| `relative_location` | 장소의 상대적 위치·전승, 2018 자료를 간략 정리 |
| `parcel_clue` | 옛 지번 단서. 현재의 똑같은 필지가 아님 |
| `location_precision` | none / relative / parcel_clue |
| `evidence_status` | source_verified / secondary_quote / hypothesis / pending |
| `source_id` | 출처 레지스트리의 ID |
| `notes` | 이체자·한계·정정 기록 |

`quoted_1911_hanja`는 **1911 원문을 직접 열람한 데이터가 아니다.** 2018 자료집이 기록한 것을 옮긴 것이다.

## 검증 규칙

- ID 중복·빈 제목·알 수 없는 지명 유형·무효 출처 ID·좌표 오탈자를 거부.
- 현대 좌표는 EPSG:4326 경위도. 외부 도구로 옮길 GeoJSON은 `[longitude,latitude]` 순서.
- 굴화리 인접한 현대 기준점도 '역사적 유구 확정 위치'로 바꾸지 않는다.
- 앞선 엑셀의 오기는 `docs/03-toponymy-and-errata.md`를 먼저 참고한다.

```bash
python scripts/validate_data.py
python scripts/export_geojson.py --output outputs/control_points.geojson
python -m unittest discover -s tests -v
```

`outputs/`는 생성물이므로 Git 추적에서 제외. 변경 이유와 검증 로그를 커밋 메시지/문서에 남긴다.
