평가 기준 data와 사례 data db를 따로 만들어서 쿼리가 들어오면 둘을 동시에 불러서 합치고 이를 전달해주는 느낌

dataloader.py > data_source에 있는 파일들을 이름으로 (평가 기준), (사례)로 나누어서 벡터db에 저장함.

retriever.py > 쿼리를 받으면 로컬 db에서 (평가 기준), (사례) document를 뽑아옴.