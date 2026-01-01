using MultimodalRAG.Services;
using MultimodalRAG.Endpoints;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() 
    { 
        Title = "Multimodal RAG API", 
        Version = "v1",
        Description = "A multimodal RAG system with Python ingestion, .NET orchestration, and Ollama local models"
    });
});

// Add HTTP client for Ollama
builder.Services.AddHttpClient<OllamaService>();

// Add our services
builder.Services.AddSingleton<VectorSearchService>();
builder.Services.AddSingleton<RAGOrchestrator>();

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Add logging
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "Multimodal RAG API v1");
        c.RoutePrefix = string.Empty; // Serve Swagger UI at root
    });
}

app.UseCors("AllowAll");

// Map all endpoints
app.MapAllEndpoints();

// Log startup information after server starts
app.Lifetime.ApplicationStarted.Register(() =>
{
    var logger = app.Services.GetRequiredService<ILogger<Program>>();
    var addresses = app.Urls;
    logger.LogInformation("🚀 Multimodal RAG API started");
    logger.LogInformation("📚 Swagger UI available at: {Url}",
        app.Environment.IsDevelopment() ? string.Join(", ", addresses) : "disabled");
    logger.LogInformation("🔗 API endpoints available at: /api/rag/*");
});

app.Run();