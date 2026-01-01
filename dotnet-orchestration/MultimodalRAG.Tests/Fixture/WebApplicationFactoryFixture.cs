using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using NSubstitute;
using MultimodalRAG.Services;

namespace MultimodalRAG.Tests.Fixtures;

public class WebApplicationFactoryFixture : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Remove real services
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(VectorSearchService));
            if (descriptor != null)
            {
                services.Remove(descriptor);
            }

            // Add mocked services
            var mockVectorSearch = Substitute.For<VectorSearchService>();
            services.AddSingleton(mockVectorSearch);
        });
    }
}
