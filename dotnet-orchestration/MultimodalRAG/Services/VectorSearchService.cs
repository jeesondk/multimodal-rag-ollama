using Npgsql;
using Pgvector;
using MultimodalRAG.Models;

namespace MultimodalRAG.Services;

public class VectorSearchService
{
    private readonly string _connectionString;
    private readonly ILogger<VectorSearchService> _logger;

    public VectorSearchService(IConfiguration configuration, ILogger<VectorSearchService> logger)
    {
        _connectionString = configuration.GetConnectionString("PostgreSQL") 
            ?? throw new InvalidOperationException("PostgreSQL connection string not configured");
        _logger = logger;
    }

    public virtual async Task<List<SearchResult>> SearchAsync(float[] queryEmbedding, int topK = 5, string? contentType = null)
    {
        var dataSourceBuilder = new NpgsqlDataSourceBuilder(_connectionString);
        dataSourceBuilder.UseVector();
        await using var dataSource = dataSourceBuilder.Build();
        await using var conn = await dataSource.OpenConnectionAsync();

        var results = new List<SearchResult>();
        var vector = new Vector(queryEmbedding);

        NpgsqlCommand cmd;
        
        if (!string.IsNullOrEmpty(contentType))
        {
            cmd = new NpgsqlCommand(@"
                SELECT id, content, metadata::text, content_type,
                       embedding <=> $1 as distance
                FROM documents
                WHERE content_type = $3
                ORDER BY embedding <=> $1
                LIMIT $2", conn);
            cmd.Parameters.AddWithValue(vector);
            cmd.Parameters.AddWithValue(topK);
            cmd.Parameters.AddWithValue(contentType);
        }
        else
        {
            cmd = new NpgsqlCommand(@"
                SELECT id, content, metadata::text, content_type,
                       embedding <=> $1 as distance
                FROM documents
                ORDER BY embedding <=> $1
                LIMIT $2", conn);
            cmd.Parameters.AddWithValue(vector);
            cmd.Parameters.AddWithValue(topK);
        }

        await using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            results.Add(new SearchResult
            {
                Id = reader.GetInt32(0),
                Content = reader.GetString(1),
                Metadata = reader.GetString(2),
                ContentType = reader.GetString(3),
                Distance = reader.GetFloat(4)
            });
        }

        _logger.LogInformation($"Found {results.Count} results for search query");
        return results;
    }

    public async Task<object> GetStatsAsync()
    {
        var dataSourceBuilder = new NpgsqlDataSourceBuilder(_connectionString);
        dataSourceBuilder.UseVector();
        await using var dataSource = dataSourceBuilder.Build();
        await using var conn = await dataSource.OpenConnectionAsync();

        var stats = new Dictionary<string, object>();

        // Total documents
        await using (var cmd = new NpgsqlCommand("SELECT COUNT(*) FROM documents", conn))
        {
            var total = await cmd.ExecuteScalarAsync();
            stats["total_documents"] = total ?? 0;
        }

        // Documents by type
        await using (var cmd = new NpgsqlCommand(@"
            SELECT content_type, COUNT(*) as count 
            FROM documents 
            GROUP BY content_type 
            ORDER BY count DESC", conn))
        {
            var byType = new Dictionary<string, int>();
            await using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                byType[reader.GetString(0)] = Convert.ToInt32(reader.GetInt64(1));
            }
            stats["documents_by_type"] = byType;
        }

        // Latest document
        await using (var cmd = new NpgsqlCommand(@"
            SELECT created_at 
            FROM documents 
            ORDER BY created_at DESC 
            LIMIT 1", conn))
        {
            var latest = await cmd.ExecuteScalarAsync();
            stats["latest_document"] = latest ?? DateTime.MinValue;
        }

        // Oldest document
        await using (var cmd = new NpgsqlCommand(@"
            SELECT created_at 
            FROM documents 
            ORDER BY created_at ASC 
            LIMIT 1", conn))
        {
            var oldest = await cmd.ExecuteScalarAsync();
            stats["oldest_document"] = oldest ?? DateTime.MinValue;
        }

        return stats;
    }
}