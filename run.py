import pandas as pd

def main():
    df = pd.read_csv("./csvs/rq1/boolean.csv")
    last_col = df.columns[-1]
    df.loc[df[last_col] > 10, last_col] = 20

    df.to_csv("lazyfix.csv", index=False)

if __name__ == "__main__":
    main()