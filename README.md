
# Driehaus Inspired Backtesting Tool

This project houses a unique backtesting tool inspired by the investment strategies of Richard Driehaus, known for his prowess in momentum investing. Utilizing a rich dataset spanning 20 years, this tool allows users to rigorously test and optimize momentum investing strategies to unveil potent insights and enhance investment decision-making.



## Getting Started

These instructions will guide you on how to get the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Ensure you have Python 3.x installed on your system. If not, download and install Python from [here](https://www.python.org/downloads/).
- It's advisable to create a virtual environment to manage dependencies for this project.

```bash
python -m venv driehaus-env
source driehaus-env/bin/activate  # On Windows, use `driehaus-env\Scripts\activate`
```

### Installation

Clone the repository to your local machine.

```bash
git clone https://github.com/your-username/driehaus-backtest.git
cd driehaus-backtest
```

Install the required packages.

```bash
pip install -r requirements.txt
```

## Usage

To delve into the various momentum investing strategies and how they perform over the 20-year span, navigate to the `Strategies` directory and run the `backtesting.py` script.

```bash
cd Strategies
python backtesting.py
```

Upon execution, `backtesting.py` will simulate the strategies and present the performance metrics for your analysis.

## Contributing

We welcome contributions! Please feel free to submit a pull request or create an issue to discuss proposed changes/enhancements.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgements

- Richard Driehaus for the inspirational momentum investing strategies.
- The community for the continuous support and contributions towards the betterment of this project.
