import type { Condition } from "../types";
import { HCCBadge } from "./HCCBadge";

interface ResultsTableProps {
  results: Condition[];
}

export function ResultsTable({ results }: ResultsTableProps) {
  const hccCount = results.filter((result) => result.hcc_relevant).length;

  return (
    <div className="results-table-wrap">
      <div className="results-summary">
        <h3>
          Results <span>{results.length}</span>
        </h3>
        <HCCBadge relevant={hccCount > 0} label={`${hccCount} HCC relevant`} />
      </div>

      <div className="table-scroll">
        <table className="results-table">
          <thead>
            <tr>
              <th scope="col">Condition</th>
              <th scope="col">ICD-10</th>
              <th scope="col">HCC</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result, index) => (
              <tr key={`${result.condition}-${result.code}-${index}`}>
                <td>{result.condition}</td>
                <td className="mono-cell">{result.code}</td>
                <td>
                  <HCCBadge relevant={result.hcc_relevant} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
