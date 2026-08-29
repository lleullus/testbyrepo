import { installReadyRuntime } from "./src/omp-adapter.js";

export default function readyTicketImplementRuntime(pi) {
  return installReadyRuntime(pi);
}

export { installReadyRuntime } from "./src/omp-adapter.js";
