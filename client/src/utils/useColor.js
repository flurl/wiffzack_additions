// useColor.js
export function useColor() {
    const colorIsDarkSimple = (color) => {
        color = (color.charAt(0) === '#') ? color.substring(1, 7) : color;
        let r = parseInt(color.substring(0, 2), 16); // hexToR
        let g = parseInt(color.substring(2, 4), 16); // hexToG
        let b = parseInt(color.substring(4, 6), 16); // hexToB
        return ((r * 0.299) + (g * 0.587) + (b * 0.114)) <= 186;
    };

    const stringToColor = (str) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        let color = '#';
        for (let i = 0; i < 3; i++) {
            let value = (hash >> (i * 8)) & 0xff;
            color += ('00' + value.toString(16)).slice(-2);
        }
        return { bg: color, fg: (colorIsDarkSimple(color) ? 'white' : 'black') };
    };

    return {
        colorIsDarkSimple,
        stringToColor,
    };
}
