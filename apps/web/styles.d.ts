/**
 * Next.js processes global stylesheet imports at build time. This declaration keeps
 * editor TypeScript servers from treating side-effect CSS imports as unresolved.
 */
declare module "*.css";
