using System.Diagnostics;
using MultimodalRAG.Models;

namespace MultimodalRAG.Services;

public class RAGOrchestrator
{
    private readonly OllamaService _ollama;
    private readonly VectorSearchService _vectorSearch;
    private readonly IConfiguration _configuration;
    private readonly ILogger<RAGOrchestrator> _logger;

    public RAGOrchestrator(
        OllamaService ollama, 
        VectorSearchService vectorSearch,
        IConfiguration configuration,
        ILogger<RAGOrchestrator> logger)
    {
        _ollama = ollama;
        _vectorSearch = vectorSearch;
        _configuration = configuration;
        _logger = logger;
    }

    public async Task<QueryResponse> QueryAsync(string userQuery, int? topK = null, string? contentType = null)
    {
        var stopwatch = Stopwatch.StartNew();
        
        // 1. Embed the query
        _logger.LogInformation("Embedding query: {Query}", userQuery);
        var queryEmbedding = await _ollama.GetEmbeddingAsync(userQuery);

        // 2. Search for relevant context
        var k = topK ?? _configuration.GetValue<int>("RAG:TopK", 5);
        _logger.LogInformation("Searching for top {TopK} results", k);
        var searchResults = await _vectorSearch.SearchAsync(queryEmbedding, k, contentType);

        // 3. Build context
        var context = string.Join("\n\n", searchResults.Select((r, i) => 
            $"[Source {i+1} - {r.ContentType}]\n{r.Content}"));

        // 4. Generate response
        var prompt = BuildPrompt(userQuery, context);
        _logger.LogInformation("Generating response");
        var answer = await _ollama.GenerateAsync(prompt);

        stopwatch.Stop();

        return new QueryResponse
        {
            Answer = answer,
            Sources = searchResults,
            ProcessingTimeMs = (int)stopwatch.ElapsedMilliseconds
        };
    }

    private string BuildPrompt(string query, string context)
    {
        return $@"You are a helpful assistant that answers questions based on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Answer the question based on the context provided
- If the context doesn't contain enough information, say so
- Be concise but comprehensive
- Cite which source(s) you're using when relevant

Answer:";
    }
}