Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$envFilePath = ".env"

If (Test-Path $envFilePath) {
    Remove-Item $envFilePath -Force
}
New-Item -Path $envFilePath -ItemType File -Force | Out-Null

Add-Content -Path $envFilePath -Value ("PROJECT_CONNECTION_STRING='" + (azd env get-value PROJECT_CONNECTION_STRING) + "'")
Add-Content -Path $envFilePath -Value ("AZURE_SEARCH_ENDPOINT=" + (azd env get-value AZURE_SEARCH_ENDPOINT))
Add-Content -Path $envFilePath -Value ("AZURE_OPENAI_ENDPOINT=" + (azd env get-value AZURE_OPENAI_ENDPOINT))
Add-Content -Path $envFilePath -Value ("AZURE_OPENAI_GPT_MODEL_NAME=" + (azd env get-value AZURE_OPENAI_GPT_MODEL_NAME))
Add-Content -Path $envFilePath -Value ("AZURE_OPENAI_EMBEDDING_MODEL_NAME=" + (azd env get-value AZURE_OPENAI_EMBEDDING_MODEL_NAME))
Add-Content -Path $envFilePath -Value ("AZURE_OPENAI_EMBEDDING_MODEL_DIMENSIONS=" + (azd env get-value AZURE_OPENAI_EMBEDDING_MODEL_DIMENSIONS))
Add-Content -Path $envFilePath -Value ("AZURE_SUBSCRIPTION_ID=" + (azd env get-value AZURE_SUBSCRIPTION_ID))
Add-Content -Path $envFilePath -Value ("AZURE_RESOURCE_GROUP=" + (azd env get-value AZURE_RESOURCE_GROUP))
Add-Content -Path $envFilePath -Value ("AZURE_AML_WORKSPACE=" + (azd env get-value AZURE_AML_WORKSPACE))

