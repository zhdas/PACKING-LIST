# MRZ 및 VIN 인식 후 Excel로 내보내는 웹 인터페이스

## 애플리케이션 기능
- 다음 입력 필드가 있는 웹사이트를 엽니다:
  - 컨테이너 번호
  - 봉인 번호
  - 차량 수량 (1~10대)
- 차량 수를 선택하면 파일 업로드 블록이 자동으로 표시됩니다:
  - 여권 사진
  - VIN 스티커 사진
- 버튼을 누르면 Excel 파일이 생성됩니다.

## 구조
- `app.py` — Flask 서버 및 Excel 생성
- `services.py` — Dynamsoft 기반 여권 및 VIN 인식
- `templates/index.html` — 웹 인터페이스

## 실행 방법
```bash
cd container_ui_app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install dynamsoft-capture-vision-bundle
python app.py

실행 후 아래 주소를 여세요:

http://127.0.0.1:5000

