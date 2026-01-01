using Microsoft.AspNetCore.Mvc;
using MultimodalRAG.Models;
using MultimodalRAG.Services;

namespace MultimodalRAG.Endpoints;

public static class OllamaEndpoints
{
    public static RouteGroupBuilder MapOllamaEndpoints(this RouteGroupBuilder group)
    {
        // Embed endpoint - Get embeddings for text
        group.MapPost("/embed", async (
            [FromBody] EmbedRequest request,
            [FromServices] OllamaService ollama,
            [FromServices] ILogger<Program> logger) =>
        {
            if (string.IsNullOrWhiteSpace(request.Text))
            {
                return Results.BadRequest(new { error = "Text cannot be empty" });
            }

            try
            {
                logger.LogInformation("Embedding text of length: {Length}", request.Text.Length);
                
                var embedding = await ollama.GetEmbeddingAsync(request.Text, request.Model);

                return Results.Ok(new
                {
                    text = request.Text,
                    model = request.Model ?? "default",
                    embedding = embedding,
                    dimension = embedding.Length
                });
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error embedding text");
                return Results.Problem(
                    detail: "An error occurred during embedding",
                    statusCode: 500
                );
            }
        })
        .WithName("Embed")
        .WithSummary("Get embeddings for text")
        .WithDescription("Returns vector embeddings for the provided text using Ollama")
        .Produces<object>(200)
        .Produces(400)
        .Produces(500);

        // Generate endpoint - Direct text generation
        group.MapPost("/generate", async (
            [FromBody] GenerateRequest request,
            [FromServices] OllamaService ollama,
            [FromServices] ILogger<Program> logger) =>
        {
            if (string.IsNullOrWhiteSpace(request.Prompt))
            {
                return Results.BadRequest(new { error = "Prompt cannot be empty" });
            }

            try
            {
                logger.LogInformation("Generating response for prompt");
                
                var response = await ollama.GenerateAsync(request.Prompt, request.Model);

                return Results.Ok(new
                {
                    prompt = request.Prompt,
                    model = request.Model ?? "default",
                    response = response
                });
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error generating response");
                return Results.Problem(
                    detail: "An error occurred during generation",
                    statusCode: 500
                );
            }
        })
        .WithName("Generate")
        .WithSummary("Generate text from prompt")
        .WithDescription("Generates text using Ollama without RAG context")
        .Produces<object>(200)
        .Produces(400)
        .Produces(500);

        return group;
    }
}