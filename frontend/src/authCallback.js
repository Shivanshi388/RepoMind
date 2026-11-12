const url = new URL(window.location.href);

if (url.searchParams.get("login") === "success") {
  url.searchParams.delete("login");
  window.location.replace(url.href);
}