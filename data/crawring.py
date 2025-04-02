from langchain.document_loaders import WebBaseLoader
file = open("./data/data_source/link_criteria.txt", "r")
url = file.read()

urls = url.split("\n")
i = 1
for url in urls:
    # 웹 문서 크롤링
    if url == "":
        continue
    docs = WebBaseLoader(url).load()
    
    file = open(f"./data/data_source/criteria_{i}.txt", "w", encoding="utf-8")
    file.write(docs[0].page_content)
    file.close()
    i += 1

