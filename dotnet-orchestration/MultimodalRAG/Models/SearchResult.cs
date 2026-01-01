namespace MultimodalRAG.Models;

public class SearchResult
{
    public int Id { get; set; }
    public string Content { get; set; } = string.Empty;
    public string Metadata { get; set; } = string.Empty;
    public string ContentType { get; set; } = string.Empty;
    public float Distance { get; set; }
}