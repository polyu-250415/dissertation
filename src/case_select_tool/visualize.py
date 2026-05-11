import json
import pandas as pd


def visualization():
    input_file = f'../data/papers/output/activity_combinations.csv'
    df = pd.read_json(input_file)

    df_exploded = (
        df
        .explode('industries', ignore_index=True)
        .explode('activities', ignore_index=True)
        .explode('technologies', ignore_index=True)
        .explode('tacit knowledge types', ignore_index=True)
    )

    # Step 3: 按三列分组并计数
    result = (
        df_exploded
        .groupby(['activity_name', 'technologies', 'tacit knowledge types'], as_index=False)
        .size()
        .rename(columns={'size': 'count'})
        .sort_values('count', ascending=False)
        .reset_index(drop=True)
    )

    # 可选：重命名列以提高可读性
    result = result.rename(columns={
        'industries': 'industry',
        'activities': 'activity',
        'technologies': 'technology',
        'tacit knowledge types': 'tacit knowledge types'
    })
    result.to_csv('../data/papers/midput/ssp_extract_relevance_3d.csv', index=False)

if __name__ == '__main__':
    visualization()