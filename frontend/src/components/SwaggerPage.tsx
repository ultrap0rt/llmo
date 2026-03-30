export function SwaggerPage() {
  return (
    <div className="h-screen w-screen bg-black">
      <iframe
        src="http://127.0.0.1:8000/api/docs/"
        title="Swagger API Docs"
        className="h-full w-full border-0"
      />
    </div>
  );
}
