namespace MultimodalRAG.Models;

public class OllamaEmbeddingRequest
{
    public string Model { get; set; } = string.Empty;
    public string Input { get; set; } = string.Empty;
}

public class OllamaEmbeddingResponse
{
    public float[][] Embeddings { get; set; } = Array.Empty<float[]>();
}

public class OllamaGenerateRequest
{
    public string Model { get; set; } = string.Empty;
    public string Prompt { get; set; } = string.Empty;
    public bool Stream { get; set; } = false;
}

public class OllamaGenerateResponse
{
    public string Response { get; set; } = string.Empty;
}