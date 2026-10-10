/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F6F5F1",
        ink: "#14171C",
        primary: {
          DEFAULT: "#1F3A93",
          light: "#3557C4",
          dark: "#152A6E",
        },
        brass: "#C8963E",
        line: "#DEDCD3",
        success: "#2F6F4E",
      },
      fontFamily: {
        display: ["'Noto Naskh Arabic'", "serif"],
        body: ["'Noto Naskh Arabic'", "serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
