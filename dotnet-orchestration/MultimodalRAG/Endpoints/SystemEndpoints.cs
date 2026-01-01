using Microsoft.AspNetCore.Mvc;
using MultimodalRAG.Services;

namespace MultimodalRAG.Endpoints;

public static class SystemEndpoints
{
    public static RouteGroupBuilder MapSystemEndpoints(this RouteGroupBuilder group)
    {
        // Health check endpoint
        group.MapGet("/health", () => Results.Ok(new
        {
            status = "healthy",
            timestamp = DateTime.UtcNow,
            version = "1.0.0",
            environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Production"
        }))
        .WithName("HealthCheck")
        .WithSummary("Check API health status")
        .WithDescription("Returns the current health status of the API")
        .Produces<object>(200);

        // Stats endpoint
        group.MapGet("/stats", async (
            [FromServices] VectorSearchService vectorSearch,
            [FromServices] ILogger<Program> logger) =>
        {
            try
            {
                var stats = await vectorSearch.GetStatsAsync();
                return Results.Ok(stats);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error getting stats");
                return Results.Problem(
                    detail: "An error occurred getting statistics",
                    statusCode: 500
                );
            }
        })
        .WithName("Stats")
        .WithSummary("Get database statistics")
        .WithDescription("Returns statistics about the document database including counts by type")
        .Produces<object>(200)
        .Produces(500);

        // Info endpoint
        group.MapGet("/info", (
            [FromServices] IConfiguration configuration) =>
        {
            return Results.Ok(new
            {
                api_version = "1.0.0",
                ollama_base_url = configuration["Ollama:BaseUrl"],
                embedding_model = configuration["Ollama:EmbeddingModel"],
                text_model = configuration["Ollama:TextModel"],
                vision_model = configuration["Ollama:VisionModel"],
                default_top_k = configuration.GetValue<int>("RAG:TopK"),
                vector_dimension = configuration.GetValue<int>("RAG:VectorDimension")
            });
        })
        .WithName("Info")
        .WithSummary("Get API configuration information")
        .WithDescription("Returns configuration details about models and settings")
        .Produces<object>(200);

        return group;
    }
}