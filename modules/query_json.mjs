export default function queryToJson(queryString) {
    if (!queryString) return {};

    const parms = new URLSearchParams(queryString);
    const result = {};

    for (const [key, value] of parms) {
        result[key] = value;
    }
    return result;
}