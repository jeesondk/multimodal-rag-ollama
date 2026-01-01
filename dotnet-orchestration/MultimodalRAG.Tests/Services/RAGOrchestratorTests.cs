using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using NFluent;
using NSubstitute;
using MultimodalRAG.Models;
using MultimodalRAG.Services;

namespace MultimodalRAG.Tests.Services;

public class RAGOrchestratorTests
{
    private readonly OllamaService _ollamaMock;
    private readonly VectorSearchService _vectorSearchMock;
    private readonly IConfiguration _configurationMock;
    private readonly ILogger<RAGOrchestrator> _loggerMock;

    public RAGOrchestratorTests()
    {
        // Create partial substitutes with required constructor arguments
        var httpClient = new HttpClient();
        var ollamaConfig = Substitute.For<IConfiguration>();
        var baseUrlSection = Substitute.For<IConfigurationSection>();
        baseUrlSection.Value.Returns("http://localhost:11434");
        ollamaConfig.GetSection("Ollama:BaseUrl").Returns(baseUrlSection);
        ollamaConfig["Ollama:BaseUrl"].Returns("http://localhost:11434");
        var ollamaLogger = Substitute.For<ILogger<OllamaService>>();
        _ollamaMock = Substitute.ForPartsOf<OllamaService>(httpClient, ollamaConfig, ollamaLogger);

        var vectorConfig = Substitute.For<IConfiguration>();
        vectorConfig.GetConnectionString("PostgreSQL").Returns("Host=localhost;Database=test");
        var vectorLogger = Substitute.For<ILogger<VectorSearchService>>();
        _vectorSearchMock = Substitute.ForPartsOf<VectorSearchService>(vectorConfig, vectorLogger);

        _configurationMock = Substitute.For<IConfiguration>();
        _loggerMock = Substitute.For<ILogger<RAGOrchestrator>>();

        // Mock the section to return the TopK value
        var section = Substitute.For<IConfigurationSection>();
        section.Value.Returns("5");
        _configurationMock.GetSection("RAG:TopK").Returns(section);
    }

    [Fact]
    public void Constructor_ShouldSucceed_WhenDependenciesProvided()
    {
        // Arrange & Act
        var orchestrator = new RAGOrchestrator(
            _ollamaMock,
            _vectorSearchMock,
            _configurationMock,
            _loggerMock
        );

        // Assert
        Check.That(orchestrator).IsNotNull();
    }
}
