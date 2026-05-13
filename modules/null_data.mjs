export default function null_data($input) {
    if ($input === '-') {
        return 0;
    } else {
        return $input;
    }
}