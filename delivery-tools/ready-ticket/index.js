import { installReadyBoundaryTools } from "./omp.js";

export * from "./src/core.js";
export { installReadyBoundaryTools } from "./omp.js";

export default function readyTicketBoundaryTools(pi) {
  return installReadyBoundaryTools(pi);
}
