module.exports = {
  extends: ["./eslint.base.js", "next/core-web-vitals", "next/typescript"],
  env: {
    node: true,
  },
  rules: {
    "@typescript-eslint/no-explicit-any": "off",
    "@typescript-eslint/no-unused-vars": [
      "warn",
      {
        "argsIgnorePattern": "^_",
        "varsIgnorePattern": "^_"
      }
    ]
  },
  "overrides": [
    {
      "files": ["**/*.ts", "**/*.tsx"],
      "rules": {
        "@typescript-eslint/no-explicit-any": "off"
      }
    }
  ]
};
