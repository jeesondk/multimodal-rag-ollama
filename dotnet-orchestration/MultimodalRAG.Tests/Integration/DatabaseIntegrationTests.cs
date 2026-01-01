using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using NFluent;
using NSubstitute;
using MultimodalRAG.Services;
using Testcontainers.PostgreSql;

namespace MultimodalRAG.Tests.Integration;

public class DatabaseIntegrationTests : IAsyncLifetime
{
    private PostgreSqlContainer? _postgresContainer;
    private VectorSearchService? _service;

    public async Task InitializeAsync()
    {
        _postgresContainer = new PostgreSqlBuilder("pgvector/pgvector:pg16")
            .WithDatabase("test_db")
            .WithUsername("test_user")
            .WithPassword("test_pass")
            .Build();

        await _postgresContainer.StartAsync();

        var configuration = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["ConnectionStrings:PostgreSQL"] = _postgresContainer.GetConnectionString()
            })
            .Build();

        var logger = Substitute.For<ILogger<VectorSearchService>>();
        _service = new VectorSearchService(configuration, logger);

        // Initialize database schema
        await InitializeDatabaseAsync();
    }

    private async Task InitializeDatabaseAsync()
    {
        await using var conn = new Npgsql.NpgsqlConnection(_postgresContainer!.GetConnectionString());
        await conn.OpenAsync();

        // Enable pgvector extension
        await using var cmd = new Npgsql.NpgsqlCommand("CREATE EXTENSION IF NOT EXISTS vector;", conn);
        await cmd.ExecuteNonQueryAsync();

        // Create documents table
        await using var createTableCmd = new Npgsql.NpgsqlCommand(@"
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(768),
                content_type VARCHAR(50),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );", conn);
        await createTableCmd.ExecuteNonQueryAsync();
    }

    public async Task DisposeAsync()
    {
        if (_postgresContainer != null)
        {
            await _postgresContainer.DisposeAsync();
        }
    }

    [Fact]
    public async Task GetStatsAsync_ShouldReturnStats()
    {
        // Arrange & Act
        var stats = await _service!.GetStatsAsync();

        // Assert
        Check.That(stats).IsNotNull();
    }
}
