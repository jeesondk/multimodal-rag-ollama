namespace MultimodalRAG.Models;

public class EmbedRequest
{
    public string Text { get; set; } = string.Empty;
    public string? Model { get; set; }
}