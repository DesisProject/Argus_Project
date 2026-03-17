import { runSimulation, SimulationRequest } from "../../services/simulationApi";

async function handleSubmit(formData: SimulationRequest) {
  try {
    const results = await runSimulation(formData);

    console.log("Year 1:", results.year1);
    console.log("Year 2:", results.year2);
    console.log("Year 3:", results.year3);

    // Render results in UI — charts, tables, etc.
  } catch (error) {
    console.error("Simulation error:", error);
  }
}