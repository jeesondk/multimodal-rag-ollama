using Microsoft.AspNetCore.Mvc;
using MultimodalRAG.Models;
using MultimodalRAG.Services;

namespace MultimodalRAG.Endpoints;

public static class RAGEndpoints
{
    public static RouteGroupBuilder MapRAGEndpoints(this RouteGroupBuilder group)
    {
        // Query endpoint - Full RAG with retrieval and generation
        group.MapPost("/query", async (
            [FromBody] QueryRequest request,
            [FromServices] RAGOrchestrator orchestrator,
            [FromServices] ILogger<Program> logger) =>
        {
            if (string.IsNullOrWhiteSpace(request.Query))
            {
                return Results.BadRequest(new { error = "Query cannot be empty" });
            }

            try
            {
                logger.LogInformation("Processing query: {Query}", request.Query);
                
                var response = await orchestrator.QueryAsync(
                    request.Query,
                    request.TopK,
                    request.ContentType);

                return Results.Ok(response);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error processing query: {Query}", request.Query);
                return Results.Problem(
                    detail: "An error occurred processing your query",
                    statusCode: 500
                );
            }
        })
        .WithName("Query")
        .WithSummary("Query the RAG system with context retrieval and generation")
        .WithDescription("Retrieves relevant documents and generates a response based on the context")
        .Produces<QueryResponse>(200)
        .Produces(400)
        .Produces(500);

        // Search endpoint - Retrieval only, no generation
        group.MapPost("/search", async (
            [FromBody] SearchRequest request,
            [FromServices] OllamaService ollama,
            [FromServices] VectorSearchService vectorSearch,
            [FromServices] ILogger<Program> logger) =>
        {
            if (string.IsNullOrWhiteSpace(request.Query))
            {
                return Results.BadRequest(new { error = "Query cannot be empty" });
            }

            try
            {
                logger.LogInformation("Searching for: {Query}", request.Query);
                
                var queryEmbedding = await ollama.GetEmbeddingAsync(request.Query);
                var results = await vectorSearch.SearchAsync(
                    queryEmbedding,
                    request.TopK ?? 5,
                    request.ContentType);

                return Results.Ok(new
                {
                    query = request.Query,
                    results = results,
                    count = results.Count
                });
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error searching: {Query}", request.Query);
                return Results.Problem(
                    detail: "An error occurred during search",
                    statusCode: 500
                );
            }
        })
        .WithName("Search")
        .WithSummary("Search for similar documents without generation")
        .WithDescription("Returns the most similar documents based on vector similarity")
        .Produces<object>(200)
        .Produces(400)
        .Produces(500);

        return group;
    }
}