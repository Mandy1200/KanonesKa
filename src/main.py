# main.py

from generator import Generator

def main():
    print("\n🤖 KanonesKa (Outbound-India Travel Compliance RAG Chatbot)")
    print("Ask any question about visas, gold/cash limits, driving, or local laws for 55 countries.")
    print("Type 'exit' to quit.\n")

    generator = Generator()

    while True:
        query = input("🧑 You: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting. Stay safe on the roads!\n")
            break

        if not query:
            print("⚠️ Please enter a valid question.\n")
            continue

        print("\n🤖 Assistant is thinking...\n")
        try:
            res = generator.ask(query)
            print("🤖 Answer:\n")
            print(res["answer"])
            print("\n📚 Sources Used:")
            for s in res.get("sources", []):
                print(f"- [{s['country']} - {s['category']}] (Score: {s['rerank_score']:.3f})")
            print("\n" + "-" * 60 + "\n")
        except Exception as e:
            print(f"⚠️ Error: {e}\n")

if __name__ == "__main__":
    main()
