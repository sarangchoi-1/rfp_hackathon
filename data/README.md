평가 기준 data와 사례 data db를 따로 만들어서 쿼리가 들어오면 둘을 동시에 불러서 합치고 이를 전달해주는 느낌

dataloader.py > data_source에 있는 파일들을 이름으로 (평가 기준), (사례)로 나누어서 벡터db에 저장함.

retriever.py > 쿼리를 받으면 로컬 db에서 (평가 기준), (사례) document를 뽑아옴.







## pdf나 txt파일로       data source에 case data는 "case_"로 이름 시작하게, criteria data는 "criteria_"로 시작하게 저장해두기

## data쪽은 그거랑 수정 요청해주시는거만 고치면 끝날 것 같습니다.