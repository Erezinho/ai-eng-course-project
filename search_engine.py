import pickle
import os
import time
from sentence_transformers import CrossEncoder
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from custom_logger import logger

    
#EMBEDDING_MODEL = "all-MiniLM-L6-v2" #MiniLM (384)
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5" #BGE-Base (768)
RERANKING_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2" #"cross-encoder/ms-marco-TinyBERT-v2" # Cross-Encoder model
PERSIST_RAG_DIR  = "local_db/rag_db"
COLLECTION_NAME = "meal_nutrition_collection"


# def load_nutritions_text_file() -> list[str]:
#         # Load all the documents form the file 'nutrition_final_for_rag.txt' into a list
#         with open('./local_db/nutrition_final_for_rag.txt', 'r') as file:
#             documents = [line for line in file.readlines()]
#         return documents

class HybridSearch():
    #solo_search_depth: int = 20
    #rerank_search_depth: int = 10

    def __init__(self):        
        meals = self.load_nutrition_meal_pkl()    
        texts, metadatas = zip(*meals)

        self.vector_store = self.build_or_load_vstore(texts, metadatas)
        self.bm25 = self.set_bm25(texts, metadatas)
        logger.info("Done initializing HybridSearch")

    def load_nutrition_meal_pkl(self) -> list[tuple[str, dict]]:
        # Load all the documents from the file 'nutrition_meal.pkl' into a list of tuples
        with open('./local_db/nutrition_meals.pkl', 'rb') as file:
            return pickle.load(file)

    def set_bm25(self, texts: list[str], metadatas: list[dict]) -> BM25Retriever:
        bm25 = BM25Retriever.from_texts(texts, metadatas)
        
        return bm25

    def build_or_load_vstore(self, texts: list[str], metadatas: list[dict]) -> Chroma:
        os.makedirs(PERSIST_RAG_DIR, exist_ok=True)
        embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # Reuse existing persisted collection if present
        if any(os.scandir(PERSIST_RAG_DIR)):
            return Chroma(collection_name=COLLECTION_NAME,
                          embedding_function=embedding_model,
                          persist_directory=PERSIST_RAG_DIR)
        
        #metadatas = [{"source_index": i} for i in range(len(documents))]
        # Add to the metadatas also the index of each document
        for i in range(len(metadatas)):
            metadatas[i]['source_index'] = i
        
        return Chroma.from_texts(
                texts=list(texts),
                embedding=embedding_model,
                metadatas=metadatas,
                collection_name=COLLECTION_NAME,
                persist_directory=PERSIST_RAG_DIR
        )

    def invoke(self, query: str, intermediate_results: int, final_results: int, print_results: bool = False) -> list[str]:
        logger.info(f"Starting 'invoke' with parameters: query='{query}', intermediate_results={intermediate_results}, final_results={final_results}")

        # Perform the initial retrieval from bm25 and vector store
        self.bm25.k = intermediate_results
        bm25_results = self.bm25.invoke(query)        
        vector_store_results = self.vector_store.similarity_search(query, k=intermediate_results)

        ensemble = EnsembleRetriever(
            retrievers=[self.bm25, self.vector_store.as_retriever(search_kwargs={"k": intermediate_results})],
            weights=[0.5, 0.5]
        )
        hybrid_results = ensemble.invoke(query)

        # Rerank the hybrid results
        reranker = CrossEncoder(RERANKING_MODEL)
        pairs = [[query, c.page_content] for c in hybrid_results]
        scores = reranker.predict(pairs)

        reranked = [
            c for _, c in sorted(zip(scores, hybrid_results), key=lambda x: x[0], reverse=True)
        ][:final_results]

        if print_results:
            self.print_results(bm25_results, vector_store_results, hybrid_results, reranked)

        #return [f"{doc.page_content} - Nutritions: {doc.metadata}" for doc in reranked]

        # convert doc.metadata to a simple string such as "calories: 100, protein: 10g"
        #for doc in reranked:
        #    doc.metadata = ", ".join(f"{key}: {value}" for key, value in doc.metadata.items() if key != "source_index")

        # Convert the results to a list of strings. Each string is composed from the 'page_content' field followed by the 'metadata' dictionary.
        # Do not include the 'source_index' field from the metadata dictionary
        final_results = []
        for doc in reranked:
            #doc.metadata.pop("source_index", None)
            nutritions = ", ".join(f"{value} {key}" for key, value in doc.metadata.items() if key in 
                                   ['calories',  'total_fat', 'saturated_fat', 'cholesterol', 'sodium', 'vitamin_b12',
                                    'vitamin_c', 'vitamin_d', 'vitamin_e', 'protein', 'fiber', 'sugars'])
            final_results.append(f"{doc.page_content} - with {nutritions}")

        logger.info(f"Ending 'invoke' with {len(final_results)} results")

        # log the final results
        for result in final_results:
            logger.info(f"Final result: {result}")

        return final_results

    def print_results(self, bm25_results, vector_store_results, hybrid_results, reranked):
        print("\n🔹 BM25 Results:")
        for doc in bm25_results:
            source_index = doc.metadata.get("source_index")
            calories = doc.metadata.get("calories", "N/A")
            print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")

        print("\n🔹 Semantic Embedding Results:")
        for doc in vector_store_results:
            source_index = doc.metadata.get("source_index")
            calories = doc.metadata.get("calories", "N/A")
            print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")

        print("\n🔹 Hybrid Results:")
        for doc in hybrid_results:
            source_index = doc.metadata.get("source_index")
            calories = doc.metadata.get("calories", "N/A")
            print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")

        print("\n🔹 Reranked Results:")
        for doc in reranked:
            source_index = doc.metadata.get("source_index")
            calories = doc.metadata.get("calories", "N/A")
            print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")

        print("\n🔹 Final:")
        for doc in reranked:
            print(f"{doc}\n")


if __name__ == "__main__":

    hybrid_search = HybridSearch()
    query = "Meatless chicken with magnesium"
    print(hybrid_search.invoke(query, 20, 1))

    query = "Provolone cheese"
    print(hybrid_search.invoke(query, 20, 1))

    # a = load_nutrition_meal_pkl()
    # for i, doc in enumerate(a):
    #      print(f"Found document {i}: {doc[0]}...\n")  # Print first 100 characters of each document
    
    # print(f"Total documents loaded: {len(a)}")
    
    #Measure the time it takes to perform a similarity search

    # meals = load_nutrition_meal_pkl()    
    # texts, metadatas = zip(*meals)
    # bm25 = BM25Retriever.from_texts(texts, metadatas)
    # bm25.k = 5

    # vector_store = build_or_load_vstore()
   
    # start_time = time.time()
    # query = "Meatless chicken with magnesium"
    # bm25_results = bm25.invoke(query)
    # print("\n🔹 BM25 Results:")
    # for doc in bm25_results:
    #     source_index = doc.metadata.get("source_index")
    #     calories = doc.metadata.get("calories", "N/A")
    #     print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")

    # candidates = vector_store.similarity_search(query, k=5)
    # end_time = time.time()
    # print("\n🔹 Semantic Embedding Results:")
    # for doc in candidates:
    #     source_index = doc.metadata.get("source_index")
    #     calories = doc.metadata.get("calories", "N/A")
    #     print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")
    # print(f"Similarity search took {end_time - start_time:.4f} seconds\n\n")
    
    # ####### 

    # start_time = time.time()
    # query = "Provolone cheese"
    # bm25_results = bm25.invoke(query)
    # print("\n\n🔹 BM25 Results:")
    # for doc in bm25_results:
    #     source_index = doc.metadata.get("source_index")
    #     calories = doc.metadata.get("calories", "N/A")
    #     print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")

    # candidates = vector_store.similarity_search(query, k=5)
    # end_time = time.time() 
    # print("\n🔹 Semantic Embedding Results:")
    # for doc in candidates:
    #     source_index = doc.metadata.get("source_index")
    #     calories = doc.metadata.get("calories", "N/A")
    #     print(f"DB index: {source_index}, Document: {doc.page_content}, Calories: {calories}")
    # print(f"Similarity search took {end_time - start_time:.4f} seconds\n\n")

    
    


    # a = load_nutritions_text_file()
    # for i, doc in enumerate(a):
    #     print(f"Found document {i}: {doc[:100]}...")  # Print first 100 characters of each document
    # print(f"Total documents loaded: {len(a)}")

