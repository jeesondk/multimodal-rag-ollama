namespace MultimodalRAG.Models;

public class QueryResponse
{
    public string Answer { get; set; } = string.Empty;
    public List<SearchResult> Sources { get; set; } = [];
    public int ProcessingTimeMs { get; set; }
}