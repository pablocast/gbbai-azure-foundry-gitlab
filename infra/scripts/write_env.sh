#!/usr/bin/env bash
envFilePath=".env"

# Remove the .env file if it exists, then create a new empty one
if [ -f "$envFilePath" ]; then
    rm "$envFilePath"
fi
touch "$envFilePath"

# Append values to the .env file
echo "PROJECT_CONNECTION_STRING='$(azd env get-value PROJECT_CONNECTION_STRING)'" >> "$envFilePath"
echo "AZURE_SEARCH_ENDPOINT=$(azd env get-value AZURE_SEARCH_ENDPOINT)" >> "$envFilePath"
echo "AZURE_OPENAI_ENDPOINT=$(azd env get-value AZURE_OPENAI_ENDPOINT)" >> "$envFilePath"
echo "AZURE_OPENAI_GPT_MODEL_NAME=$(azd env get-value AZURE_OPENAI_4o_MODEL_NAME)" >> "$envFilePath"
echo "AZURE_OPENAI_EMBEDDING_MODEL_NAME=$(azd env get-value AZURE_OPENAI_EMBEDDING_MODEL_NAME)" >> "$envFilePath"
echo "AZURE_OPENAI_EMBEDDING_MODEL_DIMENSIONS=$(azd env get-value AZURE_OPENAI_EMBEDDING_MODEL_DIMENSIONS)" >> "$envFilePath"
