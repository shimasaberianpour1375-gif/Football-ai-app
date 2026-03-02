from google import genai

PROJECT_ID = "notional-gist-474313-e1"

def main():
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="us-central1"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="Reply only with: Vertex working."
        )

        print("SUCCESS:")
        print(response.text)

    except Exception as e:
        print("ERROR:")
        print(e)

if __name__ == "__main__":
    main()