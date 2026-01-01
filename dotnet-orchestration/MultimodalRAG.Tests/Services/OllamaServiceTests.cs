using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using NFluent;
using NSubstitute;
using MultimodalRAG.Models;
using MultimodalRAG.Services;
using System.Net;
using System.Text.Json;

namespace MultimodalRAG.Tests.Services;

public class OllamaServiceTests
{
    private readonly ILogger<OllamaService> _loggerMock;
    private readonly IConfiguration _configurationMock;
    private readonly TestHttpMessageHandler _httpMessageHandler;
    private readonly HttpClient _httpClient;

    public OllamaServiceTests()
    {
        _loggerMock = Substitute.For<ILogger<OllamaService>>();
        _configurationMock = Substitute.For<IConfiguration>();
        _httpMessageHandler = new TestHttpMessageHandler();
        _httpClient = new HttpClient(_httpMessageHandler);

        // Setup configuration
        _configurationMock["Ollama:BaseUrl"].Returns("http://localhost:11434");
        _configurationMock["Ollama:EmbeddingModel"].Returns("nomic-embed-text");
        _configurationMock["Ollama:TextModel"].Returns("qwen2.5:14b");
    }

    private class TestHttpMessageHandler : HttpMessageHandler
    {
        public Func<HttpRequestMessage, CancellationToken, Task<HttpResponseMessage>>? SendAsyncFunc { get; set; }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            if (SendAsyncFunc != null)
            {
                return SendAsyncFunc(request, cancellationToken);
            }
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK));
        }
    }

    [Fact]
    public async Task GetEmbeddingAsync_ShouldReturnEmbedding_WhenSuccessful()
    {
        // Arrange
        var expectedEmbedding = new float[] { 0.1f, 0.2f, 0.3f };
        var response = new OllamaEmbeddingResponse { Embedding = expectedEmbedding };

        _httpMessageHandler.SendAsyncFunc = (request, cancellationToken) =>
            Task.FromResult(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK,
                Content = new StringContent(JsonSerializer.Serialize(response))
            });

        var service = new OllamaService(_httpClient, _configurationMock, _loggerMock);

        // Act
        var result = await service.GetEmbeddingAsync("test text");

        // Assert
        Check.That(result).ContainsExactly(expectedEmbedding);
    }

    [Fact]
    public async Task GetEmbeddingAsync_ShouldThrowException_WhenRequestFails()
    {
        // Arrange
        _httpMessageHandler.SendAsyncFunc = (request, cancellationToken) =>
            Task.FromResult(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.InternalServerError
            });

        var service = new OllamaService(_httpClient, _configurationMock, _loggerMock);

        // Act & Assert
        await Assert.ThrowsAsync<HttpRequestException>(() => service.GetEmbeddingAsync("test text"));
    }

    [Fact]
    public async Task GenerateAsync_ShouldReturnResponse_WhenSuccessful()
    {
        // Arrange
        var expectedResponse = "This is a generated response";
        var response = new OllamaGenerateResponse { Response = expectedResponse };

        _httpMessageHandler.SendAsyncFunc = (request, cancellationToken) =>
            Task.FromResult(new HttpResponseMessage
            {
                StatusCode = HttpStatusCode.OK,
                Content = new StringContent(JsonSerializer.Serialize(response))
            });

        var service = new OllamaService(_httpClient, _configurationMock, _loggerMock);

        // Act
        var result = await service.GenerateAsync("test prompt");

        // Assert
        Check.That(result).IsEqualTo(expectedResponse);
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public async Task GetEmbeddingAsync_ShouldHandleEmptyText(string text)
    {
        // Arrange
        var service = new OllamaService(_httpClient, _configurationMock, _loggerMock);

        // Act & Assert - depending on your implementation
        // You might want to throw or return empty array
        await Assert.ThrowsAnyAsync<Exception>(() => service.GetEmbeddingAsync(text));
    }
}
