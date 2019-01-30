# flake8: noqa: E501
msg_404 = """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                span#title {
                    font-size: 40px;
                    padding-bottom: 2px;
                    border-bottom: 3px solid #205493;
                }
                #federalist-explanation {
                    font-style: italic;
                }
                body {
                    font-family: "Merriweather", "Georgia", "Cambria", "Times New Roman", "Times", serif;
                }
                #content {
                    margin: 12% auto;
                }
                @media (min-width: 1025px) {
                    #content {
                        width: 60%;
                    }
                }
                @media (max-width: 1025px) {
                    #content {
                        width: 75%;
                    }
                }
                p {
                    font-size: 1.25em;
                    margin: 50px 0 40px 0;
                }
            </style>
        </head>
        <body>
            <div id="content">
                <h1>
                    <span id="title">404 / Page not found</span>
                </h1>
                <p>
                    You might want to double-check your link and try again, or return to the <a href='/'>homepage<a/>.
                </p>
                <p id="federalist-explanation">
                    This is a default 404 page for <a href='https://federalist.18f.gov'>Federalist</a>, a hosting service for federal websites.
                </p>
                <img id="federalist-logo"
                     height="30"
                     src="https://federalist.18f.gov/assets/images/federalist-logo.png"
                     alt="Federalist logo, quill inside a circle."
            </div>
        </body>
    </html>
"""
