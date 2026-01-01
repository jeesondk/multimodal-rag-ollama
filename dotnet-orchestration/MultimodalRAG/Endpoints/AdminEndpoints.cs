namespace MultimodalRAG.Endpoints;

public static class AdminEndpoints
{
    public static RouteGroupBuilder MapAdminEndpoints(this RouteGroupBuilder group)
    {
        group.MapDelete("/documents/{id}", async (int id) =>
            {
                // Delete document logic
                return Results.Ok();
            })
            .WithName("DeleteDocument")
            .WithSummary("Delete a document by ID");

        return group;
    }
}