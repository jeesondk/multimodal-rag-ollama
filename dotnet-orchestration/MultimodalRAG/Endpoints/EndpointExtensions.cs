namespace MultimodalRAG.Endpoints;

public static class EndpointExtensions
{
    public static IEndpointRouteBuilder MapAllEndpoints(this IEndpointRouteBuilder app)
    {
        var apiGroup = app.MapGroup("/api/rag")
            .WithTags("RAG");

        // Map all endpoint groups
        apiGroup.MapRAGEndpoints();
        apiGroup.MapOllamaEndpoints();
        apiGroup.MapSystemEndpoints();
        apiGroup.MapAdminEndpoints();

        return app;
    }
}