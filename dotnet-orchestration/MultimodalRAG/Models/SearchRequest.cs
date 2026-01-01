namespace MultimodalRAG.Models;

public class SearchRequest
{
    public string Query { get; set; } = string.Empty;
    public int? TopK { get; set; }
    public string? ContentType { get; set; }
}