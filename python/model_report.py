# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 15:35:57 2019

@author: shiss
"""

import pandas as pd
import numpy as np

import matplotlib.pylab as plt
from matplotlib import colors
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
from matplotlib.lines import Line2D

import seaborn as sns
import datetime


class ModelReport:
    """
    Class to visualize ADM model data exported from datamart.

    """


    def __init__(self, modelID, modelName, positives, responses, performance, snapshot):
        """
        The constructor for ModelReport class.

        All the inout data to instantiate the class must be numpy arrays.
        If ADM data is obtained in csv format, each input array for this class is the corresponding
        column in the data file. Therefore, the nth item from each parameter array belongs to one model.

        Args:
            modelID (numpy array): id of the models imported from ADM datamart
            modelName (numpy array): name of the models, usually this is PYNAME
            positives (numpy array): number of positives
            responses (numpy array): total number of responses, usually this is PYRESPONSECOUNT
            modelAUC (numpy array): model performance
            modelSnapshot (numpy array of datetime): model snapshot

        Attributes:
            cols (list of str): column names for the model pandas dataframe
            dfModel (pandas dataframe): dataframe that contains all model data
            latestModels (pandas dataframe): dataframe of only latest snapshot of each model

        Examples:
            modelID = np.array(['i1', 'i1', 'i3'])
            modelName = np.array(['model1', 'model1', 'model3'])
            positives = np.array([1, 2, 7])
            responses = np.array([100, 110, 200])
            modelAUC = np.array([0.6, 0.7, 0.73])
            modelSnapshot = np.array([datetimeObj(2019,1,1), datetimeObj(2019,2,1), datetimeObj(2019,3,1)])

            dfModel:
                | model ID | model name | positives | responses | model performance | model snapshot        |
                ---------------------------------------------------------------------------------------------
                | i1       | model1     | 1         | 100       | 0.6               | datetimeObj(2019,1,1) |
                | i1       | model1     | 2         | 110       | 0.7               | datetimeObj(2019,2,1) |
                | i3       | model3     | 7         | 200       | 0.73              | datetimeObj(2019,3,1) |

            latestModels:
                | model ID | model name | positives | responses | model performance | model snapshot        |
                ---------------------------------------------------------------------------------------------
                | i1       | model1     | 2         | 110       | 0.7               | datetimeObj(2019,2,1) |
                | i3       | model3     | 7         | 200       | 0.73              | datetimeObj(2019,3,1) |

        """
        self.modelID = modelID
        self.modelName = modelName
        self.positives = positives
        self.responses = responses
        self.modelAUC = performance
        self.modelSnapshot = snapshot
        self.cols = ['model ID', 'model name', 'positives', 'responses', 'model performance', 'model snapshot']
        self._check_data_shape()
        self.dfModel, self.latestModels = self._create_model_df()

    @staticmethod
    def _set_proper_type(df):
        """ Sets correct data type for certain dataframe columns

        """
        for col in ['model name']:
            df[col] = df[col].astype(str)
        df['model snapshot'] = pd.to_datetime(df['model snapshot'])
        return df

    def _check_data_shape(self):
        """ Ensure input data has the correct shape

        """
        if not self.modelID.shape[0]==self.modelName.shape[0]==self.positives.shape[
            0]==self.responses.shape[0]==self.modelAUC.shape[0]==self.modelSnapshot.shape[0]:
            raise TypeError("All input data must have the same number of rows")

    def _create_model_df(self):
        """ Generate model dataframes

        This method generates two pandas dataframes. One contains all the historical model data
        the other contains only the latest snapshot of each model
        Success rate is also calculated and added as a new column to both dataframes

        Returns:
            A tuple of pandas dataframes. First one is all the models. The second is latest models
        rtype: tuple

        """
        df_all = pd.DataFrame.from_dict(dict(
            zip(self.cols,[self.modelID, self.modelName, self.positives, self.responses,
                           self.modelAUC, self.modelSnapshot] )))
        df_all = self._calculate_success_rate(df_all, 'positives', 'responses', 'success rate (%)')
        df_all = self._set_proper_type(df_all)
        df_latest = df_all.sort_values('model snapshot').groupby(['model name']).tail(1)

        return (df_all, df_latest)

    @staticmethod
    def _calculate_success_rate(df, pos, total, label):
        """Given a pandas dataframe, it calculates success rate and adds as new column

        success rate = number of positive responses / total number of responses

        Args:
            df (pandas dataframe)
            pos (str): name of the positive response column
            total (str): name of the total response column
            label (str): name of the new column for success rate

        Returns:
            pandas dataframe
        """
        df[label] = 0
        df.loc[df[total]>0, label] = df[pos]*100.0/df[total]
        df.loc[df[total]<=0, label] = 0

        return df

    @staticmethod
    def _apply_query(query, df):
        """ Given an input pandas dataframe, it filters the dataframe based on input query

        Args:
            query (dict): a dict of lists where the key is column name in the dataframe and the corresponding
                   value is a list of values to keep in the dataframe
            df (pandas dataframe)

        Returns:
            filtered pandas dataframe
        """
        _df = df.drop('model ID', axis=1)
        if query!={}:
            if not type(query)==dict:
                raise TypeError('query must be a dict where values are lists')
            for key, val in query.items():
                if not type(val)==list:
                    raise ValueError('query values must be list')

            for col, val in query.items():
                _df = _df[_df[col].isin(val)]
        return _df

    @staticmethod
    def _create_sign_df(df):
        """ Generates dataframe to show whether responses decreased/increased from day to day

        For a given dataframe where columns are dates and rows are model names,
        subtracts each day's value from the previous day's value per model. Then masks the data.
        If decreased (desired situtation), it will put 1 in the cell, if no change, it will
        put 0, and if decreased it will put -1. This dataframe then could be used in the heatmap

        Args:
            df (pandas dataframe): this typically is pivoted self.dfModel

        Returns:
            pandas dataframe

        """
        vals = df.reset_index().values
        cols = df.columns
        _df = pd.DataFrame(np.hstack(
                (np.array([[vals[i,0]] for i in range(vals.shape[0])]),
                          np.array([vals[i,2:]-vals[i,1:-1]  for i in range(vals.shape[0])]))))
        _df.columns = cols
        _df.rename(columns={cols[0]:'model name'}, inplace=True)
        df_sign = _df.set_index('model name').mask(_df.set_index('model name')>0, 1)
        df_sign = df_sign.mask(df_sign<0, -1)
        df_sign[cols[0]] = 1
        return df_sign[cols].fillna(1)

    def generate_heatmap_df(self, lookback, query, fill_null_days):
        """ Generates dataframes needed to plot calendar heatmap

        The method generates two dataframes where one is used to annotate the heatmap
        and the other is used to apply colors based on the sign dataframe.
        If there are multiple snapshots per day, the latest one will be selected

        Args:
            lookback (int): defines how many days to look back at data from the last snapshot
            query (dict): dict of lists to filter dataframe
            fill_null_days (Boolean): if True, null values will be generated in the dataframe for
                                      days where there is no model snapshot

        Returns:
            tuple of annotate and sign dataframes

        """
        df = self._apply_query(query, self.dfModel)
        df = df[['model name', 'model snapshot', 'responses']].sort_values('model snapshot').reset_index(drop=True)
        df['Date'] = pd.Series([i.date() for i in df['model snapshot']])
        df = df[df['Date']>(df['Date'].max()-datetime.timedelta(lookback))]
        if df.shape[0]<1:
            print("no data within lookback range")
            return pd.DataFrame()
        else:
            idx = df.groupby(['model name', 'Date'])['model snapshot'].transform(max)==df['model snapshot']
            df = df[idx]
            if fill_null_days:
                idx_date = pd.date_range(df['Date'].min(), df['Date'].max())
                df = df.set_index('Date').groupby('model name').apply(lambda d: d.reindex(idx_date)).drop(
                    'model name', axis=1).reset_index('model name').reset_index().rename(columns={'index':'Date'})
                df['Date'] = df['Date'].dt.date
            df_annot = df.pivot(columns='Date', values='responses', index='model name')
            df_sign = self._create_sign_df(df_annot)
        return (df_annot, df_sign)

    def show_bubble_chart(self, annotate=False, sizes=(10, 2000), aspect=3,
                          b_to_anchor=(1.1,0.7), query={}, figsize=(12, 6)):
        """ Creates bubble chart similar to ADM OOTB reports

        Args:
            annotate (Boolean): If set to True, the total responses per model will be annotated
                                to the right of the bubble. All bubbles will be the same size
                                if this is set to True
            sizes (tuple): To determine how sizes are chosen when 'size' is used. 'size'
                           will not be used if annotate is set to True
            aspect (int): aspect ratio of the graph
            b_to_anchor (tuple): position of the legend
            query (dict): dict of lists to filter dataframe
            figsize (tuple): size of graph
        """
        _df = self._apply_query(query, self.latestModels)

        if annotate:
            gg = sns.relplot(x='model performance', y='success rate (%)', aspect=aspect, data=_df, hue='model name')
            ax = gg.axes[0,0]
            for idx,row in _df[['model performance', 'success rate (%)', 'responses']].sort_values(
                'responses').reset_index(drop=True).reset_index().fillna(-1).iterrows():
                if row[1]!=-1 and row[2]!=-1 and row[3]!=-1:
#                     space = (gg.ax.get_xticks()[2]-gg.ax.get_xticks()[1])/((row[0]+15)/(row[0]+1))
                    ax.text(row[1]+0.003,row[2],str(row[3]).split('.')[0], horizontalalignment='left')
            c = gg._legend.get_children()[0].get_children()[1].get_children()[0]
            c._children = c._children[0:_df['model name'].count()+1]
        else:
            gg = sns.relplot(x='model performance', y='success rate (%)', size='responses',
                             data=_df, hue='model name',  sizes=sizes, aspect=aspect)

        gg.fig.set_size_inches(figsize[0], figsize[1])
        plt.setp(gg._legend.get_texts(), fontsize='10')
        gg.ax.set_xlabel('Performance')
        gg.ax.set_xlim(0.48, 1)
        gg._legend.set_bbox_to_anchor(b_to_anchor)

    def show_response_auc_time(self, day_interval=7, query={}, figsize=(16, 10)):
        """ Shows responses and performance of models over time

        Reponses are on the y axis and the performance of the model is indicated by heatmap.
        x axis is date

        Args:
            day_interval (int): interval of tick labels along x axis
            query (dict): dict of lists to filter dataframe
            figsize (tuple): size of graph
        """
        _df_g = self._apply_query(query, self.dfModel)
        if len(_df_g['model snapshot'].unique())<2:
            'There are not enough timestamps to plot a timeline graph'
        else:
            fig, ax = plt.subplots(figsize=figsize)
            norm = colors.Normalize(vmin=0.5, vmax=1)
            mapper = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.gnuplot_r)
            for name in _df_g['model name'].unique():
                _df = _df_g[_df_g['model name']==name].sort_values('model snapshot')
                ax.plot(_df['model snapshot'].values, _df['responses'].values, color='gray')
                ax.scatter(_df['model snapshot'].values, _df['responses'].values,
                           color=[mapper.to_rgba(v) for v in _df['model performance'].values])
                if _df['responses'].max()>1:
                    ax.text(_df['model snapshot'].max(),_df['responses'].max(),'   '+name, {'FontSize':9})
            for i in ax.get_xmajorticklabels():
                i.set_rotation(90)
            ax.set_ylabel('Responses')
            ax.set_xlabel('Date')
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=day_interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m-%d"))
            ax.set_yscale('log')
            mapper._A=[]
            cbar = fig.colorbar(mapper)
            cbar.ax.get_yaxis().labelpad = 20
            cbar.ax.set_ylabel('Model Performance (AUC)')
            print('Maximum AUC across all models: %.2f' % self.dfModel['model performance'].max())

    def show_calendar_heatmap(self, lookback=15, fill_null_days=True, query={}, figsize=(14, 10)):
        """ Creates a calendar heatmap

        x axis shows model names and y axis the dates. Data in each cell is the total number
        of responses. The color indicates where responses increased/decreased or
        did not change compared to the previous day

        Args:
            lookback (int): defines how many days to look back at data from the last snapshot
            fill_null_days (Boolean): if True, null values will be generated in the dataframe for
                                      days where there is no model snapshot
            query (dict): dict of lists to filter dataframe
            figsize (tuple): size of graph
        """
        f, ax = plt.subplots(figsize=figsize)
        annot_df, heatmap_df = self.generate_heatmap_df(lookback, query, fill_null_days)
        myColors = ['r', 'orange', 'w']
        colorText = ['Decreased', 'No Change', 'Increased or NA']
        cmap = colors.ListedColormap(myColors)
        sns.heatmap(heatmap_df.T, annot=annot_df.T, mask=annot_df.T.isnull(), ax=ax,
                    linewidths=0.5, fmt='.0f', cmap=cmap, vmin=-1, vmax=1, cbar=False)
        patches = [mpatches.Patch(color=myColors[i], label=colorText[i]) for i in range(len(myColors)) ]

        legend=plt.legend(handles=patches, bbox_to_anchor=(1.05, 1),loc=2, borderaxespad=0.5, frameon=True)
        frame = legend.get_frame()
        frame.set_facecolor('lightgrey')

    def show_success_rate_time(self, day_interval=7, query={}, figsize=(16, 10)):
        """ Shows success rate of models over time

        Args:
            day_interval (int): interval of tick labels along x axis
            query (dict): dict of lists to filter dataframe
            figsize (tuple): size of graph
        """
        _df_g = self._apply_query(query, self.dfModel)
        if len(_df_g['model snapshot'].unique())<2:
            'There are not enough timestamps to plot a timeline graph'
        else:
            fig, ax = plt.subplots(figsize=figsize)
            sns.lineplot(x='model snapshot', y='success rate (%)', data=self.dfModel, hue='model name', marker="o", ax=ax)
            ax.legend(bbox_to_anchor=(1.05, 1),loc=2)
            ax.set_ylabel('Success Rate (%)')
            ax.set_xlabel('Date')
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=day_interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m-%d"))
            for i in ax.get_xmajorticklabels():
                i.set_rotation(90)

    def show_success_rate(self, query={}, figsize=(12, 8)):
        """ Shows all latest proposition success rates

        A bar plot to show the success rate of all latest model instances (propositions)
        For reading simplicity, latest success rate is also annotated next to each bar

        Args:
            query (dict): dict of lists to filter dataframe
            figsize (tuple): size of graph
        """
        f, ax = plt.subplots(figsize=figsize)
        _df_g = self._apply_query(query, self.latestModels)
        bplot = sns.barplot(x='success rate (%)', y='model name', data=_df_g.sort_values('success rate (%)', ascending=False), ax=ax)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter())
        for p in bplot.patches:
            bplot.annotate("{:0.2%}".format(p.get_width()/100.0), (p.get_width(), p.get_y()+p.get_height()/2),
                xytext=(3, 0), textcoords="offset points", ha='left', va='center')


class ADMReport(ModelReport):
    """
    Class to visualize ADM models and predictor data exported from datamart.
    This class only keeps latest model+predictor snapshots

    """

    def __init__(self, modelID, modelName, positives, responses, performance, snapshot,
                 predModelID, predName, predPerformance, binSymbol, binIndex, entryType,
                 predictorType, predSnapshot, binPositives, binResponses):
        """ Constructor of class ADMReport
        All the inout data to instantiate the class must be numpy arrays.
        If ADM data is obtained in csv format, each input array for this class is the corresponding
        column in the data file.

        Args:
            predModelID (numpy array): id of the models imported from ADM datamart predictor table
            predName (numpy array): name of the predictors, usually this is PYPREDICTORNAME
            predPerformance (numpy array): AUC of the predictors. Note that this is different from
                "performance" argument which is model performance.
            binSymbol (numpy array): label of predictor bins, PYBINSYMBOLS
            binIndex (numpy array): Index of predictor bins
            entryType (numpy array): predictor status identifier PYENTRYTYPE
            predictorType (numpy array): predictor type (symbolic vs numeric) PYTYPE
            predSnapshot (numpy array of datetime): predictor snapshot
            binPositives (numpy array): number of positives within bins
            binResponses (numpy array): total number of responses within bins

        Attributes:
            predCols (list): name of columns in predictor dataframe

        """
        ModelReport.__init__(self, modelID, modelName, positives, responses, performance, snapshot)
        self.predModelID = predModelID
        self.predName = predName
        self.predPerformance = predPerformance
        self.binSymbol = binSymbol
        self.binIndex = binIndex
        self.entryType = entryType
        self.predictorType = predictorType
        self.predSnapshot = predSnapshot
        self.binPositives = binPositives
        self.binResponses = binResponses
        self._check_pred_data_shape()
        self.predCols = ['model ID', 'predictor name', 'predictor performance', 'bin symbol', 'bin index', 'entry type',
                         'predictor type', 'bin positives', 'bin responses', 'predictor snapshot']
        self.latestPredModel = self._create_pred_model_df()


    def _check_pred_data_shape(self):
        """ Ensure input data has the correct shape

        """
        if not self.predModelID.shape[0]==self.predName.shape[0]==self.predPerformance.shape[0]==self.binSymbol.shape[0]==self.binIndex.shape[0
                    ]==self.entryType.shape[0]==self.predictorType.shape[0]==self.predSnapshot.shape[0]==self.binPositives.shape[0]==self.binResponses.shape[0]:
            raise TypeError("All input data must have the same number of rows")

    def _create_pred_model_df(self):
        """
        This method generates a pandas dataframes that contains all latest predictor data
        merged with latest model snapshot.
        bin propensity is also calculated and added as a new column

        Returns:
            pandas dataframe
        """
        _df = pd.DataFrame.from_dict(dict(
                zip(self.predCols, [self.predModelID, self.predName, self.predPerformance, self.binSymbol, self.binIndex,
                    self.entryType, self.predictorType, self.binPositives, self.binResponses, self.predSnapshot])))
        idx = _df.groupby(['model ID', 'predictor name'])['predictor snapshot'].transform(max)==_df['predictor snapshot']
        _df = _df[idx]
        _df = self._calculate_success_rate(_df, 'bin positives', 'bin responses', 'bin propensity')
        latestPredModel = self.dfModel.merge(_df, on='model ID', how='left').drop(['model ID', 'predictor snapshot'], axis=1)
        return latestPredModel

    def show_score_distribution(self, models=None, figsize=(14, 10)):
        """ Show score distribution similar to ADM out-of-the-box report

        Shows a score distribution graph per model. If certain models selected,
        only those models will be shown.
        the only difference between this graph and the one shown on ADM
        report is that, here the raw number of responses are shown on left y-axis whereas in
        ADM reports, the percentage of responses are shown

        Args:
            models (list): select certain model names to show score distribution
            figsize (tuple): size of graph
        """

        df = self.latestPredModel[self.latestPredModel['predictor name']=='Classifier']
        if models:
            df = df[df['model name'].isin(models)]
        for model in df['model name'].unique():
            _df = df[df['model name']==model]
            self.distribution_graph(_df, 'Model name: '+model, figsize)

    @staticmethod
    def distribution_graph(df, title, figsize):
        """ generic method to generate distribution graphs given data and graph size

        Args:
            df (Pandas dataframe)
            title (str): title of graph
            figsize (tuple): size of graph
        """
        order = df.sort_values('bin index')['bin symbol']
        fig, ax = plt.subplots(figsize=figsize)
        sns.barplot(x='bin symbol', y='bin responses', data=df, ax=ax, color='blue', order=order)
        ax1 = ax.twinx()
        sns.catplot(x='bin symbol', y='bin propensity', data=df, ax=ax1, color='orange', kind='point', order=order)
        for i in ax.get_xmajorticklabels():
            i.set_rotation(90)
        labels = [i.get_text()[0:24]+'...' if len(i.get_text())>25 else i.get_text() for i in ax.get_xticklabels()]
        ax.set_xticklabels(labels)
        ax.set_ylabel('Responses')
        ax.set_xlabel('Range')
        ax1.set_ylabel('Propensity (%)')
        patches = [mpatches.Patch(color='blue', label='Responses'), mpatches.Patch(color='orange', label='Propensity')]
        ax.legend(handles=patches, bbox_to_anchor=(1.05, 1),loc=2, borderaxespad=0.5, frameon=True)
        ax.set_title(title)
        plt.close()

    def show_predictor_report(self, model_name, predictors=None, figsize=(10, 5)):
        """ Show predictor graphs for a given model

        For a given model (model_name) shows all its predictors' graphs. If certain predictors
        selected, only those predictor graphs will be shown

        Args:
            model_name (str): name of the model
            predictors (list): list of predictors to show their graphs. Optional field
            figsize (tuple): size of graph
        """
        df = self.latestPredModel[(self.latestPredModel['model name']==model_name) &
                                  (self.latestPredModel['predictor name']!='Classifier')]
        if predictors:
            df = df[df['predictor name'].isin(predictors)]
        for pred in df['predictor name'].unique():
            _df = df[df['predictor name']==pred]
            title = 'Model name: '+model_name+'\n Predictor name: '+pred
            self.distribution_graph(_df, title, figsize)

    def show_predictor_performance_boxplot(self, figsize=(6, 12)):
        """ Shows a box plot of predictor performance
        """
        fig, ax = plt.subplots(figsize=figsize)
        _df_g = self.latestPredModel[self.latestPredModel['predictor name']!='Classifier'].reset_index(drop=True)
        _df_g['legend'] = pd.Series([i.split('.')[0] if len(i.split('.'))>1 else 'Primary' for i in _df_g['predictor name']])
        order = _df_g.groupby('predictor name')['predictor performance'].mean().fillna(0).sort_values()[::-1].index
        sns.boxplot(x='predictor performance', y='predictor name', data=_df_g, order=order, ax=ax)
        ax.set_xlabel('Predictor Performance')
        ax.set_ylabel('Predictor Name')

        norm = colors.Normalize(vmin=0, vmax=len(_df_g['legend'].unique())-1)
        mapper = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.gnuplot_r)
        cl_dict = dict(zip(_df_g['legend'].unique(), [mapper.to_rgba(v) for v in range(len(_df_g['legend'].unique()))]))
        value_dict = dict(_df_g[['predictor name', 'legend']].drop_duplicates().values)
        type_dict = dict(_df_g[['predictor name', 'predictor type']].drop_duplicates().values)
        boxes = ax.artists
        for i in range(len(boxes)):
            boxes[i].set_facecolor(cl_dict[value_dict[order[i]]])
            if type_dict[order[i]].lower()=='symbolic':
                boxes[i].set_linestyle('--')

        lines = [Line2D([], [], label='Numeric', color='black', linewidth=1.5),
                 Line2D([], [], label='Symbolic', color='black', linewidth=1.5, linestyle='--')]
        legend_type = plt.legend(handles=lines, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.5,
                  frameon=True, title='Predictor Type \n')
        patches = [mpatches.Patch(color=j, label=i) for i, j in cl_dict.items()]
        legend = plt.legend(handles=patches, bbox_to_anchor=(1.05, 0.85), loc=2, borderaxespad=0.5,
                  frameon=True, title='Predictor Source \n')
        plt.gca().add_artist(legend_type)
        legend._legend_box.align = "left"
        legend_type._legend_box.align = "left"

    def show_model_predictor_performance_heatmap(self, figsize=(14, 10)):
        """ Shows a heatmap plot of predictor performance across models
        """
        _df_g = self.latestPredModel[self.latestPredModel['predictor name']!='Classifier'].reset_index(drop=True)[[
            'model name', 'predictor name', 'predictor performance']].drop_duplicates().pivot(
            index='model name', columns='predictor name', values='predictor performance')
        order = list(self.latestPredModel[self.latestPredModel['predictor name']!='Classifier'][[
            'model name', 'predictor name', 'predictor performance']].drop_duplicates().groupby(
            'predictor name')['predictor performance'].mean().fillna(0).sort_values()[::-1].index)
        _df_g = _df_g[order]*100.0
        x_order = list(self.latestPredModel[self.latestPredModel['predictor name']!='Classifier'][[
            'model name', 'predictor name', 'predictor performance']].drop_duplicates().groupby(
            'model name')['predictor performance'].mean().fillna(0).sort_values()[::-1].index)
        df_g = _df_g.reindex(x_order)
        cmap = colors.LinearSegmentedColormap.from_list(
            'mycmap', [(0/100.0, 'red'), (20/100.0, 'green'),
                       (90/100.0, 'white'), (100/100.0, 'white')])
        f, ax = plt.subplots(figsize=figsize)
        sns.heatmap(df_g.fillna(50).T, ax=ax, cmap=cmap, annot=True, fmt='.2f', vmin=50, vmax=100)
