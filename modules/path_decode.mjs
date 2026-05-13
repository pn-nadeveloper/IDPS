export default function decodePath(fullPath) {
    try {
        return decodeURIComponent(fullPath);
    } catch (e) {
        return fullPath;
    }
}