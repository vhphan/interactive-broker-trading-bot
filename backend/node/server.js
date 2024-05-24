// basic Express server
import express from 'express';
import {init} from "./my_ib/client.js";

const app = express();
const port = 3000;

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(port, () => {
        console.log(`Example app listening at http://localhost:${port}`);
        init().catch((err) => {
            console.error(err);
        });
    }
);