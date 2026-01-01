using MultimodalRAG.Models;

namespace MultimodalRAG.Services;

public class OllamaService
{
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _config;
    private readonly ILogger<OllamaService> _logger;
    private readonly string _baseUrl;
    
    public OllamaService(HttpClient httpClient, IConfiguration config, ILogger<OllamaService> logger)
    {
        _httpClient = httpClient;
        _config = config;
        _logger = logger;
        _baseUrl = _config["Ollama:BaseUrl"] ?? "http://localhost:11434";
    }

    public virtual async Task<float[]> GetEmbeddingAsync(string text, string? model = null)
    {
        model ??= _config["Ollama:EmbeddingModel"];

        var request = new OllamaEmbeddingRequest
        {
            Model = model!,
            Prompt = text
        };

        try
        {
            var response = await _httpClient.PostAsJsonAsync($"{_baseUrl}/api/embeddings", request);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<OllamaEmbeddingResponse>();
            return result?.Embedding ?? Array.Empty<float>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting embedding from Ollama");
            throw;
        }
    }

    public virtual async Task<string> GenerateAsync(string prompt, string? model = null)
    {
        model ??= _config["Ollama:TextModel"];

        var request = new OllamaGenerateRequest
        {
            Model = model!,
            Prompt = prompt,
            Stream = false
        };

        try
        {
            var response = await _httpClient.PostAsJsonAsync($"{_baseUrl}/api/generate", request);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<OllamaGenerateResponse>();
            return result?.Response ?? string.Empty;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating text from Ollama");
            throw;
        }
    }
}