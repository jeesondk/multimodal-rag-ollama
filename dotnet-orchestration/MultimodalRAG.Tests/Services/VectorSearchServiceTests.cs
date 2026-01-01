using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using NFluent;
using NSubstitute;
using MultimodalRAG.Services;

namespace MultimodalRAG.Tests.Services;

public class VectorSearchServiceTests
{
    private readonly IConfiguration _configurationMock;
    private readonly ILogger<VectorSearchService> _loggerMock;

    public VectorSearchServiceTests()
    {
        _configurationMock = Substitute.For<IConfiguration>();
        _loggerMock = Substitute.For<ILogger<VectorSearchService>>();
    }

    [Fact]
    public void Constructor_ShouldThrowException_WhenConnectionStringMissing()
    {
        // Arrange
        _configurationMock.GetConnectionString("PostgreSQL").Returns((string?)null);

        // Act & Assert
        var exception = Assert.Throws<InvalidOperationException>(() =>
            new VectorSearchService(_configurationMock, _loggerMock));

        Check.That(exception.Message).Contains("PostgreSQL connection string not configured");
    }

    [Fact]
    public void Constructor_ShouldSucceed_WhenConnectionStringProvided()
    {
        // Arrange
        _configurationMock
            .GetConnectionString("PostgreSQL")
            .Returns("Host=localhost;Database=test");

        // Act
        var service = new VectorSearchService(_configurationMock, _loggerMock);

        // Assert
        Check.That(service).IsNotNull();
    }
}
