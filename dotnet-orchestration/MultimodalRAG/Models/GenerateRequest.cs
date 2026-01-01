namespace MultimodalRAG.Models;

public class GenerateRequest
{
    public string Prompt { get; set; } = string.Empty;
    public string? Model { get; set; }
}